import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  IconButton,
  Alert,
  AlertTitle,
  Stack,
  Divider,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
  Save as SaveIcon,
  Schedule as ScheduleIcon,
  Email as EmailIcon,
  PictureAsPdf as PdfIcon,
  TableChart as CsvIcon,
  Event as EventIcon,
  AccessTime as TimeIcon,
  Send as SendIcon,
} from '@mui/icons-material';
import axios from 'axios';

/**
 * Schedule configuration interface
 */
interface ScheduleConfig {
  frequency: 'daily' | 'weekly' | 'monthly';
  day_of_week?: number; // 0-6 (Sunday-Saturday) for weekly
  day_of_month?: number; // 1-31 for monthly
  hour: number; // 0-23
  minute: number; // 0-59
}

/**
 * Delivery configuration interface
 */
interface DeliveryConfig {
  format: 'pdf' | 'csv' | 'both';
  include_charts: boolean;
  include_summary: boolean;
}

/**
 * Report configuration interface
 */
interface ReportConfiguration {
  metrics: string[];
  filters: Record<string, any>;
}

/**
 * Scheduled report interface
 */
interface ScheduledReport {
  id: string;
  name: string;
  organization_id?: string;
  report_id?: string;
  configuration: ReportConfiguration;
  schedule_config: ScheduleConfig;
  delivery_config: DeliveryConfig;
  recipients: string[];
  is_active: boolean;
  next_run_at?: string;
  created_at: string;
  updated_at?: string;
}

/**
 * Form data for creating/editing scheduled reports
 */
interface ScheduledReportFormData {
  name: string;
  metrics: string[];
  frequency: 'daily' | 'weekly' | 'monthly';
  day_of_week: number;
  day_of_month: number;
  hour: number;
  minute: number;
  format: 'pdf' | 'csv' | 'both';
  include_charts: boolean;
  include_summary: boolean;
  recipients: string;
  is_active: boolean;
}

/**
 * Available metrics for reports
 */
const AVAILABLE_METRICS = [
  { id: 'time_to_hire', name: 'Time to Hire', category: 'performance' },
  { id: 'resumes_processed', name: 'Resumes Processed', category: 'pipeline' },
  { id: 'match_rates', name: 'Match Rates', category: 'performance' },
  { id: 'source_effectiveness', name: 'Source Effectiveness', category: 'sourcing' },
  { id: 'funnel_conversion', name: 'Funnel Conversion', category: 'pipeline' },
  { id: 'diversity_metrics', name: 'Diversity Metrics', category: 'diversity' },
  { id: 'recruiter_performance', name: 'Recruiter Performance', category: 'performance' },
];

/**
 * ScheduledReportsManager Component Props
 */
interface ScheduledReportsManagerProps {
  /** Organization ID for filtering */
  organizationId?: string;
  /** API base URL */
  apiUrl?: string;
  /** Callback when reports are modified */
  onReportChange?: () => void;
}

/**
 * ScheduledReportsManager Component
 *
 * Provides a comprehensive interface for managing scheduled analytics reports.
 * Features include:
 * - View all scheduled reports
 * - Create new scheduled reports with delivery settings
 * - Edit existing schedules
 * - Delete scheduled reports
 * - Configure schedule frequency, time, format, and recipients
 * - Toggle report active/inactive status
 *
 * @example
 * ```tsx
 * <ScheduledReportsManager
 *   organizationId="org-123"
 *   onReportChange={() => console.log('Reports updated')}
 * />
 * ```
 */
const ScheduledReportsManager: React.FC<ScheduledReportsManagerProps> = ({
  organizationId,
  apiUrl = '/api/reports',
  onReportChange,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scheduledReports, setScheduledReports] = useState<ScheduledReport[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [reportToDelete, setReportToDelete] = useState<ScheduledReport | null>(null);
  const [editingReport, setEditingReport] = useState<ScheduledReport | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [formData, setFormData] = useState<ScheduledReportFormData>({
    name: '',
    metrics: ['time_to_hire'],
    frequency: 'weekly',
    day_of_week: 1, // Monday
    day_of_month: 1,
    hour: 9,
    minute: 0,
    format: 'pdf',
    include_charts: true,
    include_summary: true,
    recipients: '',
    is_active: true,
  });

  /**
   * Fetch scheduled reports from backend
   */
  const fetchScheduledReports = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Note: This endpoint needs to be implemented in the backend
      // For now, we'll use mock data
      const response = await axios.get(`${apiUrl}/schedule`, {
        params: organizationId ? { organization_id: organizationId } : {},
      });

      setScheduledReports(response.data.schedules || []);
    } catch (err) {
      // Use mock data for development
      const mockReports: ScheduledReport[] = [
        {
          id: '1',
          name: 'Weekly Analytics Report',
          configuration: {
            metrics: ['time_to_hire', 'resumes_processed', 'match_rates'],
            filters: {},
          },
          schedule_config: {
            frequency: 'weekly',
            day_of_week: 1,
            hour: 9,
            minute: 0,
          },
          delivery_config: {
            format: 'pdf',
            include_charts: true,
            include_summary: true,
          },
          recipients: ['manager@example.com'],
          is_active: true,
          next_run_at: '2024-03-25T09:00:00Z',
          created_at: '2024-03-01T10:00:00Z',
        },
      ];
      setScheduledReports(mockReports);
    } finally {
      setLoading(false);
    }
  }, [apiUrl, organizationId]);

  useEffect(() => {
    fetchScheduledReports();
  }, [fetchScheduledReports]);

  /**
   * Open create dialog
   */
  const handleCreate = () => {
    setEditingReport(null);
    setFormData({
      name: '',
      metrics: ['time_to_hire'],
      frequency: 'weekly',
      day_of_week: 1,
      day_of_month: 1,
      hour: 9,
      minute: 0,
      format: 'pdf',
      include_charts: true,
      include_summary: true,
      recipients: '',
      is_active: true,
    });
    setDialogOpen(true);
  };

  /**
   * Open edit dialog
   */
  const handleEdit = (report: ScheduledReport) => {
    setEditingReport(report);
    setFormData({
      name: report.name,
      metrics: report.configuration.metrics,
      frequency: report.schedule_config.frequency,
      day_of_week: report.schedule_config.day_of_week || 1,
      day_of_month: report.schedule_config.day_of_month || 1,
      hour: report.schedule_config.hour,
      minute: report.schedule_config.minute,
      format: report.delivery_config.format,
      include_charts: report.delivery_config.include_charts,
      include_summary: report.delivery_config.include_summary,
      recipients: report.recipients.join(', '),
      is_active: report.is_active,
    });
    setDialogOpen(true);
  };

  /**
   * Handle form submit
   */
  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);

    try {
      // Validate form
      if (!formData.name.trim()) {
        setError('Report name is required');
        setSubmitting(false);
        return;
      }

      if (formData.metrics.length === 0) {
        setError('At least one metric must be selected');
        setSubmitting(false);
        return;
      }

      if (!formData.recipients.trim()) {
        setError('At least one recipient email is required');
        setSubmitting(false);
        return;
      }

      // Parse recipients
      const recipientsList = formData.recipients
        .split(',')
        .map((email) => email.trim())
        .filter((email) => email.length > 0);

      // Validate email format
      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      for (const email of recipientsList) {
        if (!emailPattern.test(email)) {
          setError(`Invalid email address: ${email}`);
          setSubmitting(false);
          return;
        }
      }

      // Build request payload
      const payload = {
        name: formData.name,
        organization_id: organizationId,
        report_id: editingReport?.report_id,
        configuration: {
          metrics: formData.metrics,
          filters: {},
        },
        schedule_config: {
          frequency: formData.frequency,
          day_of_week: formData.frequency === 'weekly' ? formData.day_of_week : undefined,
          day_of_month: formData.frequency === 'monthly' ? formData.day_of_month : undefined,
          hour: formData.hour,
          minute: formData.minute,
        },
        delivery_config: {
          format: formData.format,
          include_charts: formData.include_charts,
          include_summary: formData.include_summary,
        },
        recipients: recipientsList,
        is_active: formData.is_active,
      };

      if (editingReport) {
        // Update existing report
        await axios.put(`${apiUrl}/schedule/${editingReport.id}`, payload);
      } else {
        // Create new report
        await axios.post(`${apiUrl}/schedule`, payload);
      }

      // Refresh list
      await fetchScheduledReports();

      // Close dialog
      setDialogOpen(false);

      // Notify parent
      if (onReportChange) {
        onReportChange();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : `Failed to ${editingReport ? 'update' : 'create'} scheduled report`;
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Handle delete confirmation
   */
  const handleDeleteConfirm = (report: ScheduledReport) => {
    setReportToDelete(report);
    setDeleteDialogOpen(true);
  };

  /**
   * Handle delete
   */
  const handleDelete = async () => {
    if (!reportToDelete) return;

    setSubmitting(true);
    setError(null);

    try {
      await axios.delete(`${apiUrl}/schedule/${reportToDelete.id}`);

      // Refresh list
      await fetchScheduledReports();

      // Close dialog
      setDeleteDialogOpen(false);
      setReportToDelete(null);

      // Notify parent
      if (onReportChange) {
        onReportChange();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to delete scheduled report';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Format frequency display
   */
  const formatFrequency = (schedule: ScheduleConfig): string => {
    const hourStr = schedule.hour.toString().padStart(2, '0');
    const minuteStr = schedule.minute.toString().padStart(2, '0');
    const time = `${hourStr}:${minuteStr}`;

    if (schedule.frequency === 'daily') {
      return `Daily at ${time}`;
    } else if (schedule.frequency === 'weekly') {
      const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      const day = days[schedule.day_of_week || 0];
      return `Weekly on ${day} at ${time}`;
    } else {
      const dayNum = schedule.day_of_month || 1;
      const suffix = dayNum === 1 ? 'st' : dayNum === 2 ? 'nd' : dayNum === 3 ? 'rd' : 'th';
      return `Monthly on ${dayNum}${suffix} at ${time}`;
    }
  };

  /**
   * Format next run time
   */
  const formatNextRun = (nextRunAt?: string): string => {
    if (!nextRunAt) return 'Not scheduled';

    try {
      const date = new Date(nextRunAt);
      return date.toLocaleString();
    } catch {
      return 'Invalid date';
    }
  };

  /**
   * Get format icon
   */
  const getFormatIcon = (format: string) => {
    if (format === 'pdf') return <PdfIcon color="error" />;
    if (format === 'csv') return <CsvIcon color="success" />;
    return <EmailIcon />;
  };

  return (
    <Box>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={2}>
            <ScheduleIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                {t('scheduledReports.title', { defaultValue: 'Scheduled Reports' })}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('scheduledReports.subtitle', {
                  defaultValue: 'Manage automated report delivery schedules',
                })}
              </Typography>
            </Box>
          </Box>
          <Stack direction="row" spacing={2}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchScheduledReports}
              disabled={loading}
            >
              {t('common.refresh', { defaultValue: 'Refresh' })}
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreate}
            >
              {t('scheduledReports.createNew', { defaultValue: 'New Schedule' })}
            </Button>
          </Stack>
        </Stack>
      </Paper>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          <AlertTitle>{t('common.error', { defaultValue: 'Error' })}</AlertTitle>
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading && (
        <Box display="flex" justifyContent="center" py={8}>
          <CircularProgress />
        </Box>
      )}

      {/* Empty State */}
      {!loading && scheduledReports.length === 0 && (
        <Paper elevation={1} sx={{ p: 6, textAlign: 'center' }}>
          <ScheduleIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {t('scheduledReports.empty.title', { defaultValue: 'No Scheduled Reports' })}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {t('scheduledReports.empty.message', {
              defaultValue: 'Create your first scheduled report to receive automated analytics updates.',
            })}
          </Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
            {t('scheduledReports.createFirst', { defaultValue: 'Create First Schedule' })}
          </Button>
        </Paper>
      )}

      {/* Scheduled Reports List */}
      {!loading && scheduledReports.length > 0 && (
        <Grid container spacing={3}>
          {scheduledReports.map((report) => (
            <Grid item xs={12} md={6} lg={4} key={report.id}>
              <Card elevation={2}>
                <CardContent>
                  {/* Report Header */}
                  <Stack direction="row" alignItems="flex-start" justifyContent="space-between" mb={2}>
                    <Box flex={1}>
                      <Typography variant="h6" gutterBottom>
                        {report.name}
                      </Typography>
                      <Chip
                        label={report.is_active ? 'Active' : 'Inactive'}
                        color={report.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>
                    <Box>
                      {getFormatIcon(report.delivery_config.format)}
                    </Box>
                  </Stack>

                  <Divider sx={{ my: 2 }} />

                  {/* Schedule Info */}
                  <Stack spacing={1.5}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <EventIcon fontSize="small" color="action" />
                      <Typography variant="body2">
                        {formatFrequency(report.schedule_config)}
                      </Typography>
                    </Box>

                    <Box display="flex" alignItems="center" gap={1}>
                      <TimeIcon fontSize="small" color="action" />
                      <Typography variant="body2" color="text.secondary">
                        Next run: {formatNextRun(report.next_run_at)}
                      </Typography>
                    </Box>

                    <Box display="flex" alignItems="center" gap={1}>
                      <EmailIcon fontSize="small" color="action" />
                      <Typography variant="body2" color="text.secondary">
                        {report.recipients.length} recipient{report.recipients.length !== 1 ? 's' : ''}
                      </Typography>
                    </Box>

                    {/* Metrics */}
                    <Box>
                      <Typography variant="caption" color="text.secondary" display="block" mb={0.5}>
                        Metrics:
                      </Typography>
                      <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                        {report.configuration.metrics.slice(0, 3).map((metric) => (
                          <Chip key={metric} label={metric} size="small" variant="outlined" />
                        ))}
                        {report.configuration.metrics.length > 3 && (
                          <Chip
                            label={`+${report.configuration.metrics.length - 3}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Stack>
                    </Box>
                  </Stack>
                </CardContent>

                <CardActions sx={{ justifyContent: 'flex-end', px: 2, pb: 2 }}>
                  <IconButton
                    size="small"
                    onClick={() => handleEdit(report)}
                    aria-label="Edit"
                  >
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteConfirm(report)}
                    aria-label="Delete"
                    color="error"
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create/Edit Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Typography variant="h6">
              {editingReport
                ? t('scheduledReports.edit', { defaultValue: 'Edit Scheduled Report' })
                : t('scheduledReports.create', { defaultValue: 'Create Scheduled Report' })}
            </Typography>
            <IconButton onClick={() => setDialogOpen(false)} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>

        <Divider />

        <DialogContent>
          <Stack spacing={3} sx={{ mt: 2 }}>
            {/* Report Name */}
            <TextField
              fullWidth
              label={t('scheduledReports.form.name', { defaultValue: 'Report Name' })}
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              disabled={submitting}
            />

            {/* Metrics Selection */}
            <FormControl fullWidth required disabled={submitting}>
              <InputLabel>{t('scheduledReports.form.metrics', { defaultValue: 'Metrics' })}</InputLabel>
              <Select
                multiple
                value={formData.metrics}
                onChange={(e) => setFormData({ ...formData, metrics: e.target.value as string[] })}
                label="Metrics"
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {AVAILABLE_METRICS.map((metric) => (
                  <MenuItem key={metric.id} value={metric.id}>
                    {metric.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Frequency */}
            <FormControl fullWidth required disabled={submitting}>
              <InputLabel>{t('scheduledReports.form.frequency', { defaultValue: 'Frequency' })}</InputLabel>
              <Select
                value={formData.frequency}
                onChange={(e) => setFormData({ ...formData, frequency: e.target.value as any })}
                label="Frequency"
              >
                <MenuItem value="daily">Daily</MenuItem>
                <MenuItem value="weekly">Weekly</MenuItem>
                <MenuItem value="monthly">Monthly</MenuItem>
              </Select>
            </FormControl>

            {/* Day of Week (for weekly) */}
            {formData.frequency === 'weekly' && (
              <FormControl fullWidth disabled={submitting}>
                <InputLabel>{t('scheduledReports.form.dayOfWeek', { defaultValue: 'Day of Week' })}</InputLabel>
                <Select
                  value={formData.day_of_week}
                  onChange={(e) => setFormData({ ...formData, day_of_week: e.target.value as number })}
                  label="Day of Week"
                >
                  <MenuItem value={0}>Sunday</MenuItem>
                  <MenuItem value={1}>Monday</MenuItem>
                  <MenuItem value={2}>Tuesday</MenuItem>
                  <MenuItem value={3}>Wednesday</MenuItem>
                  <MenuItem value={4}>Thursday</MenuItem>
                  <MenuItem value={5}>Friday</MenuItem>
                  <MenuItem value={6}>Saturday</MenuItem>
                </Select>
              </FormControl>
            )}

            {/* Day of Month (for monthly) */}
            {formData.frequency === 'monthly' && (
              <TextField
                fullWidth
                type="number"
                label={t('scheduledReports.form.dayOfMonth', { defaultValue: 'Day of Month' })}
                value={formData.day_of_month}
                onChange={(e) => setFormData({ ...formData, day_of_month: parseInt(e.target.value) || 1 })}
                inputProps={{ min: 1, max: 31 }}
                disabled={submitting}
              />
            )}

            {/* Time */}
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  type="number"
                  label={t('scheduledReports.form.hour', { defaultValue: 'Hour (0-23)' })}
                  value={formData.hour}
                  onChange={(e) => setFormData({ ...formData, hour: parseInt(e.target.value) || 0 })}
                  inputProps={{ min: 0, max: 23 }}
                  disabled={submitting}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  type="number"
                  label={t('scheduledReports.form.minute', { defaultValue: 'Minute (0-59)' })}
                  value={formData.minute}
                  onChange={(e) => setFormData({ ...formData, minute: parseInt(e.target.value) || 0 })}
                  inputProps={{ min: 0, max: 59 }}
                  disabled={submitting}
                />
              </Grid>
            </Grid>

            {/* Format */}
            <FormControl fullWidth required disabled={submitting}>
              <InputLabel>{t('scheduledReports.form.format', { defaultValue: 'Export Format' })}</InputLabel>
              <Select
                value={formData.format}
                onChange={(e) => setFormData({ ...formData, format: e.target.value as any })}
                label="Export Format"
              >
                <MenuItem value="pdf">PDF</MenuItem>
                <MenuItem value="csv">CSV</MenuItem>
                <MenuItem value="both">Both (PDF + CSV)</MenuItem>
              </Select>
            </FormControl>

            {/* Options */}
            <Stack spacing={1}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.include_charts}
                    onChange={(e) => setFormData({ ...formData, include_charts: e.target.checked })}
                    disabled={submitting}
                  />
                }
                label={t('scheduledReports.form.includeCharts', { defaultValue: 'Include Charts' })}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.include_summary}
                    onChange={(e) => setFormData({ ...formData, include_summary: e.target.checked })}
                    disabled={submitting}
                  />
                }
                label={t('scheduledReports.form.includeSummary', { defaultValue: 'Include Summary' })}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    disabled={submitting}
                  />
                }
                label={t('scheduledReports.form.isActive', { defaultValue: 'Active' })}
              />
            </Stack>

            {/* Recipients */}
            <TextField
              fullWidth
              label={t('scheduledReports.form.recipients', { defaultValue: 'Recipients (comma-separated emails)' })}
              value={formData.recipients}
              onChange={(e) => setFormData({ ...formData, recipients: e.target.value })}
              placeholder="manager@example.com, hr@example.com"
              required
              multiline
              rows={2}
              disabled={submitting}
              helperText="Separate multiple email addresses with commas"
            />
          </Stack>
        </DialogContent>

        <Divider />

        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button onClick={() => setDialogOpen(false)} disabled={submitting}>
            {t('common.cancel', { defaultValue: 'Cancel' })}
          </Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={20} /> : <SaveIcon />}
          >
            {submitting
              ? t('common.saving', { defaultValue: 'Saving...' })
              : editingReport
              ? t('common.update', { defaultValue: 'Update' })
              : t('common.create', { defaultValue: 'Create' })}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
      >
        <DialogTitle>
          {t('scheduledReports.delete.title', { defaultValue: 'Delete Scheduled Report?' })}
        </DialogTitle>
        <DialogContent>
          <Typography>
            {t('scheduledReports.delete.message', {
              defaultValue: 'Are you sure you want to delete this scheduled report? This action cannot be undone.',
            })}
          </Typography>
          {reportToDelete && (
            <Typography fontWeight={600} mt={2}>
              {reportToDelete.name}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={submitting}>
            {t('common.cancel', { defaultValue: 'Cancel' })}
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleDelete}
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={20} /> : <DeleteIcon />}
          >
            {submitting
              ? t('common.deleting', { defaultValue: 'Deleting...' })
              : t('common.delete', { defaultValue: 'Delete' })}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ScheduledReportsManager;
