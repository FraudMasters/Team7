/**
 * Audit Retention Settings Page
 *
 * Provides comprehensive audit log retention policy management including:
 * - Current retention policy overview
 * - Configure retention period (90 days, 1 year, 7 years)
 * - View audit log statistics
 * - Compliance information for different retention periods
 *
 * Accessible at /admin/audit-retention
 *
 * @example
 * ```tsx
 * <AuditRetentionSettings />
 * ```
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Snackbar,
  CircularProgress,
  Paper,
  Divider,
  Stack,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives/Icon';
import { format } from 'date-fns';
import auditRetentionApi, { type AuditRetentionConfig } from '../../services/auditRetentionApi';

/**
 * Retention period options with compliance information
 */
const RETENTION_PERIODS = [
  {
    value: 90,
    label: '90 days',
    description: 'Minimum retention for basic compliance',
    compliance: 'Suitable for most operational needs',
  },
  {
    value: 365,
    label: '1 year',
    description: 'Standard retention for financial compliance',
    compliance: 'SOC 2, ISO 27001',
  },
  {
    value: 2555,
    label: '7 years',
    description: 'Extended retention for regulatory compliance',
    compliance: 'GDPR, HIPAA, financial regulations',
  },
];

/**
 * AuditRetentionSettings Page Component
 */
export function AuditRetentionSettings() {
  const [config, setConfig] = useState<AuditRetentionConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedRetentionDays, setSelectedRetentionDays] = useState<number>(90);
  const [hasChanges, setHasChanges] = useState(false);

  /**
   * Load retention configuration from API
   */
  const fetchConfig = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await auditRetentionApi.getRetentionConfig();
      setConfig(data);
      setSelectedRetentionDays(data.retention_days);
      setHasChanges(false);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load retention configuration';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Save retention configuration to API
   */
  const handleSaveConfig = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const updatedConfig = await auditRetentionApi.updateRetentionConfig({
        retention_days: selectedRetentionDays,
      });
      setConfig(updatedConfig);
      setSuccess('Retention policy updated successfully');
      setHasChanges(false);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to save retention configuration';
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  /**
   * Handle retention period change
   */
  const handleRetentionChange = (value: number) => {
    setSelectedRetentionDays(value);
    setHasChanges(config ? value !== config.retention_days : true);
  };

  /**
   * Get selected retention period details
   */
  const getSelectedPeriod = () => {
    return RETENTION_PERIODS.find((p) => p.value === selectedRetentionDays);
  };

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  const selectedPeriod = getSelectedPeriod();

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box mb={4}>
        <Box display="flex" alignItems="center" gap={1} mb={1}>
          <Icon name="history" size={32} />
          <Typography variant="h4">Audit Log Retention Settings</Typography>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Configure how long audit logs are retained for compliance and security purposes
        </Typography>
      </Box>

      {/* Overview Cards */}
      {config && (
        <Grid container spacing={3} mb={4}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  <Icon name="clock" color="primary" />
                  <Typography variant="h6">Current Retention</Typography>
                </Box>
                <Typography variant="h3" color="primary">
                  {RETENTION_PERIODS.find((p) => p.value === config.retention_days)?.label ||
                    `${config.retention_days} days`}
                </Typography>
                <Typography variant="body2" color="text.secondary" mt={1}>
                  Logs older than this will be automatically deleted
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  <Icon name="database" color="secondary" />
                  <Typography variant="h6">Total Logs</Typography>
                </Box>
                <Typography variant="h3" color="secondary">
                  {config.total_logs.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary" mt={1}>
                  Audit log entries currently stored
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  <Icon name="calendar" color="info" />
                  <Typography variant="h6">Oldest Log</Typography>
                </Box>
                <Typography variant="h3" color="info">
                  {config.oldest_log_at
                    ? format(new Date(config.oldest_log_at), 'MMM d, yyyy')
                    : 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" mt={1}>
                  {config.last_cleanup_at
                    ? `Last cleanup: ${format(new Date(config.last_cleanup_at), 'MMM d, yyyy')}`
                    : 'No cleanup performed yet'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Configuration Form */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Retention Policy Configuration
        </Typography>
        <Divider sx={{ my: 2 }} />

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel id="retention-period-label">Retention Period</InputLabel>
              <Select
                labelId="retention-period-label"
                value={selectedRetentionDays}
                label="Retention Period"
                onChange={(e) => handleRetentionChange(e.target.value as number)}
              >
                {RETENTION_PERIODS.map((period) => (
                  <MenuItem key={period.value} value={period.value}>
                    {period.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {selectedPeriod && (
            <Grid item xs={12}>
              <Alert severity="info">
                <Typography variant="subtitle2" gutterBottom>
                  {selectedPeriod.description}
                </Typography>
                <Typography variant="body2">
                  <strong>Compliance:</strong> {selectedPeriod.compliance}
                </Typography>
              </Alert>
            </Grid>
          )}

          <Grid item xs={12}>
            <Alert severity="warning">
              <Typography variant="subtitle2" gutterBottom>
                Important: Data Deletion
              </Typography>
              <Typography variant="body2">
                Changing the retention period will not immediately delete logs. Cleanup runs automatically
                based on the scheduled task. Logs older than the retention period will be permanently deleted
                and cannot be recovered.
              </Typography>
            </Alert>
          </Grid>
        </Grid>

        <Box mt={3} display="flex" gap={2}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<Icon name="save" />}
            onClick={handleSaveConfig}
            disabled={!hasChanges || saving}
          >
            {saving ? 'Saving...' : 'Save Configuration'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<Icon name="refresh-cw" />}
            onClick={fetchConfig}
            disabled={loading || saving}
          >
            Refresh
          </Button>
        </Box>
      </Paper>

      {/* Compliance Information */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Compliance Guidelines
        </Typography>
        <Divider sx={{ my: 2 }} />
        <Stack spacing={2}>
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              SOC 2 / ISO 27001
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Requires audit logs to be retained for at least 1 year to demonstrate security controls
              and access monitoring.
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              GDPR
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Audit logs may contain personal data and must be retained only as long as necessary for
              the purpose (typically 1-7 years for compliance purposes).
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              HIPAA
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Requires audit logs for electronic protected health information (ePHI) to be retained
              for at least 6 years.
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Financial Services
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Many financial regulations require audit trail retention of 7 years for transaction
              records and access logs.
            </Typography>
          </Box>
        </Stack>
      </Paper>

      {/* Success Snackbar */}
      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity="success" onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      </Snackbar>

      {/* Error Snackbar */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </Container>
  );
}

export default AuditRetentionSettings;
