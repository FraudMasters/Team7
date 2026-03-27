import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Alert,
  AlertTitle,
  Stack,
  Divider,
  Grid,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Switch,
  FormControlLabel,
  Chip,
  FormHelperText,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Close as CloseIcon,
  Save as SaveIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Schedule as ScheduleIcon,
  Edit as EditIcon,
  PlayArrow as PlayArrowIcon,
} from '@mui/icons-material';
import { ApiClient } from '@/api/client';
import {
  ReportsClient,
  ReportScheduleFrequency,
  ReportFormat,
  ReportType,
  type ScheduledReportCreate,
  type ScheduledReportUpdate,
  type ScheduledReportResponse,
  type ScheduledReportListResponse,
  type ReportListResponse,
  type ScheduleConfig,
  type DeliveryConfig,
} from '@/api/reports';

/**
 * Day of week mapping for schedule configuration
 */
const DAYS_OF_WEEK = [
  { value: 0, label: 'Sunday' },
  { value: 1, label: 'Monday' },
  { value: 2, label: 'Tuesday' },
  { value: 3, label: 'Wednesday' },
  { value: 4, label: 'Thursday' },
  { value: 5, label: 'Friday' },
  { value: 6, label: 'Saturday' },
];

/**
 * Hours for time selection (0-23)
 */
const HOURS = Array.from({ length: 24 }, (_, i) => i);

/**
 * Days of month for monthly schedule (1-31)
 */
const DAYS_OF_MONTH = Array.from({ length: 31 }, (_, i) => i + 1);

/**
 * ReportScheduler Component Props
 */
interface ReportSchedulerProps {
  /** Callback when a schedule is created or updated */
  onScheduleSave?: (schedule: ScheduledReportResponse) => void;
  /** Callback when a schedule is deleted */
  onScheduleDelete?: (scheduleId: string) => void;
  /** API client instance */
  apiClient?: ApiClient;
  /** Organization ID filter */
  organizationId?: string;
}

/**
 * Form state for creating/editing scheduled reports
 */
interface ScheduleFormState {
  name: string;
  reportId: string;
  frequency: ReportScheduleFrequency;
  hour: number;
  minute: number;
  dayOfWeek?: number;
  dayOfMonth?: number;
  timezone: string;
  format: ReportFormat;
  includeCharts: boolean;
  includeSummary: boolean;
  emailSubject: string;
  emailBody: string;
  recipients: string[];
  isActive: boolean;
}

/**
 * Default form state
 */
const DEFAULT_FORM_STATE: ScheduleFormState = {
  name: '',
  reportId: '',
  frequency: ReportScheduleFrequency.Weekly,
  hour: 9,
  minute: 0,
  dayOfWeek: 1, // Monday
  timezone: 'UTC',
  format: ReportFormat.PDF,
  includeCharts: true,
  includeSummary: true,
  emailSubject: '',
  emailBody: '',
  recipients: [],
  isActive: true,
};

/**
 * ReportScheduler Component
 *
 * Provides a comprehensive interface for scheduling automated report generation and delivery.
 * Features include:
 * - View existing scheduled reports
 * - Create new scheduled reports with flexible timing options
 * - Edit existing schedules
 * - Configure delivery settings (format, email content)
 * - Manage recipient lists
 * - Enable/disable schedules
 * - Delete schedules
 *
 * @example
 * ```tsx
 * <ReportScheduler
 *   organizationId="org-123"
 *   onScheduleSave={(schedule) => console.log('Saved', schedule)}
 * />
 * ```
 */
const ReportScheduler: React.FC<ReportSchedulerProps> = ({
  onScheduleSave,
  onScheduleDelete,
  apiClient,
  organizationId,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Data state
  const [schedules, setSchedules] = useState<ScheduledReportResponse[]>([]);
  const [reports, setReports] = useState<ReportListResponse['reports']>([]);

  // Form state
  const [formOpen, setFormOpen] = useState(false);
  const [editingScheduleId, setEditingScheduleId] = useState<string | null>(null);
  const [formState, setFormState] = useState<ScheduleFormState>(DEFAULT_FORM_STATE);
  const [recipientInput, setRecipientInput] = useState('');

  // Initialize API client
  const client = apiClient || new ApiClient();
  const reportsClient = new ReportsClient(client);

  /**
   * Fetch scheduled reports and available reports
   */
  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch scheduled reports
      const schedulesResponse: ScheduledReportListResponse =
        await reportsClient.listScheduledReports(organizationId);
      setSchedules(schedulesResponse.scheduled_reports || []);

      // Fetch available reports for dropdown
      const reportsResponse: ReportListResponse =
        await reportsClient.listReports(organizationId);
      setReports(reportsResponse.reports || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load scheduled reports';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Load data on mount
   */
  useEffect(() => {
    fetchData();
  }, [organizationId]);

  /**
   * Open form for creating a new schedule
   */
  const handleCreateNew = () => {
    setEditingScheduleId(null);
    setFormState(DEFAULT_FORM_STATE);
    setFormOpen(true);
  };

  /**
   * Open form for editing an existing schedule
   */
  const handleEdit = (schedule: ScheduledReportResponse) => {
    setEditingScheduleId(schedule.id);
    setFormState({
      name: schedule.name,
      reportId: schedule.report_id,
      frequency: schedule.schedule_config.frequency as ReportScheduleFrequency,
      hour: schedule.schedule_config.hour,
      minute: schedule.schedule_config.minute || 0,
      dayOfWeek: schedule.schedule_config.day_of_week,
      dayOfMonth: schedule.schedule_config.day_of_month,
      timezone: schedule.schedule_config.timezone || 'UTC',
      format: schedule.delivery_config.format as ReportFormat,
      includeCharts: schedule.delivery_config.include_charts ?? true,
      includeSummary: schedule.delivery_config.include_summary ?? true,
      emailSubject: schedule.delivery_config.email_subject || '',
      emailBody: schedule.delivery_config.email_body || '',
      recipients: schedule.recipients || [],
      isActive: schedule.is_active,
    });
    setFormOpen(true);
  };

  /**
   * Close the form dialog
   */
  const handleCloseForm = () => {
    setFormOpen(false);
    setEditingScheduleId(null);
    setFormState(DEFAULT_FORM_STATE);
    setRecipientInput('');
  };

  /**
   * Update form field
   */
  const updateField = <K extends keyof ScheduleFormState>(
    field: K,
    value: ScheduleFormState[K]
  ) => {
    setFormState((prev) => ({ ...prev, [field]: value }));
  };

  /**
   * Add recipient email
   */
  const handleAddRecipient = () => {
    const email = recipientInput.trim();
    if (email && !formState.recipients.includes(email)) {
      // Basic email validation
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        setError('Please enter a valid email address');
        return;
      }
      updateField('recipients', [...formState.recipients, email]);
      setRecipientInput('');
      setError(null);
    }
  };

  /**
   * Remove recipient email
   */
  const handleRemoveRecipient = (email: string) => {
    updateField(
      'recipients',
      formState.recipients.filter((r) => r !== email)
    );
  };

  /**
   * Save the schedule (create or update)
   */
  const handleSave = async () => {
    // Validation
    if (!formState.name.trim()) {
      setError('Schedule name is required');
      return;
    }
    if (!formState.reportId) {
      setError('Please select a report');
      return;
    }
    if (formState.recipients.length === 0) {
      setError('Please add at least one recipient');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const scheduleConfig: ScheduleConfig = {
        frequency: formState.frequency,
        hour: formState.hour,
        minute: formState.minute,
        day_of_week: formState.dayOfWeek,
        day_of_month: formState.dayOfMonth,
        timezone: formState.timezone,
      };

      const deliveryConfig: DeliveryConfig = {
        format: formState.format,
        include_charts: formState.includeCharts,
        include_summary: formState.includeSummary,
        email_subject: formState.emailSubject || undefined,
        email_body: formState.emailBody || undefined,
      };

      let savedSchedule: ScheduledReportResponse;

      if (editingScheduleId) {
        // Update existing schedule
        const updateData: ScheduledReportUpdate = {
          name: formState.name,
          schedule_config: scheduleConfig,
          delivery_config: deliveryConfig,
          recipients: formState.recipients,
          is_active: formState.isActive,
        };
        savedSchedule = await reportsClient.updateScheduledReport(
          editingScheduleId,
          updateData
        );
        setSuccessMessage('Schedule updated successfully');
      } else {
        // Create new schedule
        if (!organizationId) {
          setError('Organization ID is required to create a schedule');
          return;
        }
        const createData: ScheduledReportCreate = {
          organization_id: organizationId,
          report_id: formState.reportId,
          name: formState.name,
          schedule_config: scheduleConfig,
          delivery_config: deliveryConfig,
          recipients: formState.recipients,
          is_active: formState.isActive,
        };
        savedSchedule = await reportsClient.createScheduledReport(createData);
        setSuccessMessage('Schedule created successfully');
      }

      // Refresh the list
      await fetchData();

      // Close form
      handleCloseForm();

      // Callback
      if (onScheduleSave) {
        onScheduleSave(savedSchedule);
      }

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to save schedule';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  /**
   * Delete a schedule
   */
  const handleDelete = async (scheduleId: string) => {
    if (!confirm('Are you sure you want to delete this schedule?')) {
      return;
    }

    setSaving(true);
    setError(null);

    try {
      await reportsClient.deleteScheduledReport(scheduleId);
      await fetchData();
      setSuccessMessage('Schedule deleted successfully');

      if (onScheduleDelete) {
        onScheduleDelete(scheduleId);
      }

      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to delete schedule';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  /**
   * Toggle schedule active status
   */
  const handleToggleActive = async (schedule: ScheduledReportResponse) => {
    setSaving(true);
    setError(null);

    try {
      const updateData: ScheduledReportUpdate = {
        is_active: !schedule.is_active,
      };
      await reportsClient.updateScheduledReport(schedule.id, updateData);
      await fetchData();
      setSuccessMessage(
        `Schedule ${!schedule.is_active ? 'enabled' : 'disabled'} successfully`
      );
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to update schedule status';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  /**
   * Format schedule frequency for display
   */
  const formatFrequency = (schedule: ScheduledReportResponse): string => {
    const config = schedule.schedule_config;
    const time = `${config.hour.toString().padStart(2, '0')}:${(config.minute || 0)
      .toString()
      .padStart(2, '0')}`;

    switch (config.frequency) {
      case ReportScheduleFrequency.Daily:
        return `Daily at ${time}`;
      case ReportScheduleFrequency.Weekly:
        const dayName =
          DAYS_OF_WEEK.find((d) => d.value === config.day_of_week)?.label ||
          'Unknown';
        return `Weekly on ${dayName} at ${time}`;
      case ReportScheduleFrequency.Monthly:
        return `Monthly on day ${config.day_of_month || 1} at ${time}`;
      default:
        return 'Unknown frequency';
    }
  };

  /**
   * Format next run time
   */
  const formatNextRun = (schedule: ScheduledReportResponse): string => {
    if (!schedule.next_run_at) return 'Not scheduled';
    const date = new Date(schedule.next_run_at);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h1">
          <ScheduleIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Report Schedules
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchData}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateNew}
          >
            Create Schedule
          </Button>
        </Stack>
      </Box>

      {/* Success Message */}
      {successMessage && (
        <Alert severity="success" onClose={() => setSuccessMessage(null)} sx={{ mb: 2 }}>
          {successMessage}
        </Alert>
      )}

      {/* Error Message */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          <AlertTitle>Error</AlertTitle>
          {error}
        </Alert>
      )}

      {/* Schedules List */}
      {schedules.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary" paragraph>
            No scheduled reports yet.
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateNew}
          >
            Create Your First Schedule
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {schedules.map((schedule) => {
            const report = reports.find((r) => r.id === schedule.report_id);
            return (
              <Grid item xs={12} md={6} lg={4} key={schedule.id}>
                <Card>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                      <Typography variant="h6" component="h3">
                        {schedule.name}
                      </Typography>
                      <Chip
                        label={schedule.is_active ? 'Active' : 'Inactive'}
                        color={schedule.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Stack spacing={1}>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Report:</strong> {report?.name || 'Unknown'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Frequency:</strong> {formatFrequency(schedule)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Format:</strong> {schedule.delivery_config.format.toUpperCase()}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Next Run:</strong> {formatNextRun(schedule)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Recipients:</strong> {schedule.recipients.length}
                      </Typography>
                    </Stack>

                    <Divider sx={{ my: 2 }} />

                    <Stack direction="row" spacing={1} justifyContent="flex-end">
                      <IconButton
                        size="small"
                        onClick={() => handleEdit(schedule)}
                        disabled={saving}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleToggleActive(schedule)}
                        disabled={saving}
                        color={schedule.is_active ? 'default' : 'success'}
                      >
                        <PlayArrowIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(schedule.id)}
                        disabled={saving}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Create/Edit Dialog */}
      <Dialog
        open={formOpen}
        onClose={handleCloseForm}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingScheduleId ? 'Edit Schedule' : 'Create Schedule'}
          <IconButton
            onClick={handleCloseForm}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          <Stack spacing={3}>
            {/* Name */}
            <TextField
              label="Schedule Name"
              value={formState.name}
              onChange={(e) => updateField('name', e.target.value)}
              fullWidth
              required
              helperText="A descriptive name for this schedule"
            />

            {/* Report Selection */}
            <FormControl fullWidth required>
              <InputLabel>Report</InputLabel>
              <Select
                value={formState.reportId}
                onChange={(e) => updateField('reportId', e.target.value)}
                label="Report"
              >
                {reports.map((report) => (
                  <MenuItem key={report.id} value={report.id}>
                    {report.name} ({report.report_type})
                  </MenuItem>
                ))}
              </Select>
              <FormHelperText>Select the report to schedule</FormHelperText>
            </FormControl>

            <Divider />
            <Typography variant="h6">Schedule Configuration</Typography>

            {/* Frequency */}
            <FormControl fullWidth required>
              <InputLabel>Frequency</InputLabel>
              <Select
                value={formState.frequency}
                onChange={(e) =>
                  updateField('frequency', e.target.value as ReportScheduleFrequency)
                }
                label="Frequency"
              >
                <MenuItem value={ReportScheduleFrequency.Daily}>Daily</MenuItem>
                <MenuItem value={ReportScheduleFrequency.Weekly}>Weekly</MenuItem>
                <MenuItem value={ReportScheduleFrequency.Monthly}>Monthly</MenuItem>
              </Select>
            </FormControl>

            {/* Day of Week (for Weekly) */}
            {formState.frequency === ReportScheduleFrequency.Weekly && (
              <FormControl fullWidth>
                <InputLabel>Day of Week</InputLabel>
                <Select
                  value={formState.dayOfWeek || 1}
                  onChange={(e) => updateField('dayOfWeek', Number(e.target.value))}
                  label="Day of Week"
                >
                  {DAYS_OF_WEEK.map((day) => (
                    <MenuItem key={day.value} value={day.value}>
                      {day.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}

            {/* Day of Month (for Monthly) */}
            {formState.frequency === ReportScheduleFrequency.Monthly && (
              <FormControl fullWidth>
                <InputLabel>Day of Month</InputLabel>
                <Select
                  value={formState.dayOfMonth || 1}
                  onChange={(e) => updateField('dayOfMonth', Number(e.target.value))}
                  label="Day of Month"
                >
                  {DAYS_OF_MONTH.map((day) => (
                    <MenuItem key={day} value={day}>
                      {day}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}

            {/* Time */}
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <FormControl fullWidth>
                  <InputLabel>Hour</InputLabel>
                  <Select
                    value={formState.hour}
                    onChange={(e) => updateField('hour', Number(e.target.value))}
                    label="Hour"
                  >
                    {HOURS.map((hour) => (
                      <MenuItem key={hour} value={hour}>
                        {hour.toString().padStart(2, '0')}:00
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label="Timezone"
                  value={formState.timezone}
                  onChange={(e) => updateField('timezone', e.target.value)}
                  fullWidth
                  helperText="e.g., UTC, America/New_York"
                />
              </Grid>
            </Grid>

            <Divider />
            <Typography variant="h6">Delivery Configuration</Typography>

            {/* Format */}
            <FormControl fullWidth required>
              <InputLabel>Export Format</InputLabel>
              <Select
                value={formState.format}
                onChange={(e) => updateField('format', e.target.value as ReportFormat)}
                label="Export Format"
              >
                <MenuItem value={ReportFormat.PDF}>PDF</MenuItem>
                <MenuItem value={ReportFormat.Excel}>Excel</MenuItem>
                <MenuItem value={ReportFormat.CSV}>CSV</MenuItem>
              </Select>
            </FormControl>

            {/* Options */}
            <Stack spacing={1}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formState.includeCharts}
                    onChange={(e) => updateField('includeCharts', e.target.checked)}
                  />
                }
                label="Include Charts"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formState.includeSummary}
                    onChange={(e) => updateField('includeSummary', e.target.checked)}
                  />
                }
                label="Include Summary"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formState.isActive}
                    onChange={(e) => updateField('isActive', e.target.checked)}
                  />
                }
                label="Active"
              />
            </Stack>

            {/* Email Settings */}
            <TextField
              label="Email Subject (Optional)"
              value={formState.emailSubject}
              onChange={(e) => updateField('emailSubject', e.target.value)}
              fullWidth
              helperText="Custom email subject line"
            />
            <TextField
              label="Email Body (Optional)"
              value={formState.emailBody}
              onChange={(e) => updateField('emailBody', e.target.value)}
              fullWidth
              multiline
              rows={3}
              helperText="Custom email message"
            />

            <Divider />
            <Typography variant="h6">Recipients</Typography>

            {/* Add Recipient */}
            <Box display="flex" gap={1}>
              <TextField
                label="Email Address"
                value={recipientInput}
                onChange={(e) => setRecipientInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddRecipient();
                  }
                }}
                fullWidth
                placeholder="user@example.com"
              />
              <Button
                variant="outlined"
                onClick={handleAddRecipient}
                startIcon={<AddIcon />}
              >
                Add
              </Button>
            </Box>

            {/* Recipients List */}
            {formState.recipients.length > 0 && (
              <Paper variant="outlined" sx={{ maxHeight: 200, overflow: 'auto' }}>
                <List dense>
                  {formState.recipients.map((email) => (
                    <ListItem key={email}>
                      <ListItemText primary={email} />
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          size="small"
                          onClick={() => handleRemoveRecipient(email)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              </Paper>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseForm}>Cancel</Button>
          <Button
            variant="contained"
            startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
            onClick={handleSave}
            disabled={saving}
          >
            {editingScheduleId ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ReportScheduler;
